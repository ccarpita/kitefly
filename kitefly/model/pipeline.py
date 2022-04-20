from typing import Union

from .command import Command
from .group import Group
from .step import Step
from .target import Target
from .wait import Wait

from ..filter.filter import Filter


def filter_include(filter: Filter, items: list, item: Union[Step, Group]):
    if isinstance(item, Step):
        if filter(item):
            items.append(item)
    elif isinstance(item, Group):
        filtered_items: list[Step] = []
        for group_item in item.items:
            filter_include(filter, filtered_items, group_item)
        if not filtered_items:
            return
        items.append(Group(*filtered_items))


class Pipeline:
    """
    Methods for manipulating entire pipelines of steps, including
    the important role of rendering a de-duplicated properly
    ordered collection via steps(), or filtering based on
    targets and tags.
    """

    def __init__(self, *steps: Union[Step, Group]):
        self.items: list[Union[Step, Group]] = list(steps)

    def __iadd__(self, value: Union[Step, Group]):
        self.items.append(value)

    def filtered(self, filter: Filter) -> "Pipeline":
        """
        Filter the pipeline with the optional provided values and return a flattened
        list of steps with duplicate steps (via key) removed.
        """
        filtered: list[Union[Step, Group]] = []
        for item in self.items:
            filter_include(filter, filtered, item)
        return Pipeline(*filtered)

    def steps(self) -> list[Step]:
        """
        Flatten nested group structure into a list of Step objects where:
        1. Steps with keys (Command steps) will be de-duplicated, such that the last instance
           of that Step in the list is preserved
        2. Multiple Wait steps in a row will be removed from the beginning/end of the step list
        """
        # (1) Flatten
        # Iterate through items and flatten Groups into a one-dimensional list of Step objects
        steps: list[Step] = []
        for item in self.items:
            coll: list[Step] = []
            if isinstance(item, Step):
                coll = [item]
            elif isinstance(item, Group):
                coll = item.steps()
            for step in coll:
                steps.append(step)

        # (2) Dependent Inclusion
        # Iterate through all steps and ensure all dependents are added to the list of steps,
        # even if they weren't in the list of steps added directly to the pipeline
        seen: set[Step] = set()
        queue: list[Step] = []
        while queue or not seen:
            for dep in queue:
                steps.append(dep)
            queue = []
            for step in steps:
                if step not in seen:
                    seen.add(step)
                    for dep in step.dependents:
                        if dep not in seen:
                            seen.add(dep)
                            queue.append(dep)

        # (3) Clean depends_on
        # Remove any depends_on keys for filtered-out steps
        keys = set([step.key for step in steps if isinstance(step, Command)])
        for step in steps:
            step.depends_on = [key for key in step.depends_on if key in keys]

        # (4) De-duplicate
        # Remove duplicate steps and only preserve the final instance of that
        # step in the list.
        steps.reverse()
        uniq: list[Step] = []
        seen = set()
        for step in steps:
            if isinstance(step, Wait) or step not in seen:
                uniq.append(step)
                seen.add(step)
        uniq.reverse()
        steps = uniq

        # (5) Remove unnecessary Waits
        # Remove runs of identical wait steps, and strip waits from the beginning/end
        # of the pipeline
        last_step = None
        cleaned: list[Step] = []
        for step in steps:
            is_valid = True
            if isinstance(step, Wait):
                is_valid = last_step is not None and last_step != step
            last_step = step
            if is_valid:
                cleaned.append(step)
        if isinstance(steps[-1], Wait):
            steps.pop()

        return steps

    def targets(self) -> list[Target]:
        """
        Return the unique set of targets for the current Pipeline
        """
        seen: set[Target] = set()
        for step in self.steps():
            for target in step.get_targets():
                seen.add(target)
        return list(seen)

    def asdict(self) -> dict:
        return {"steps": [s.asdict() for s in self.steps()]}

    def asyaml(self) -> str:
        import yaml

        return yaml.dump(self.asdict())
