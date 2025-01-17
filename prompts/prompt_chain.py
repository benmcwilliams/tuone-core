from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable
from enum import Enum

class ProjectStage(Enum):
    TECH = "tech"
    COMPONENT = "component"
    EXPANSION = "expansion"
    INVESTMENT = "investment"
    CAPACITY = "capacity"
    STATUS = "status"
    DATES = "dates"

@dataclass
class PromptTemplate:
    template: str
    model: str  # Specific fine-tuned model ID
    validation: Optional[Callable] = None
    dependencies: list[ProjectStage] = None

class PromptChain:
    def __init__(self):
        self.prompts = {
            ProjectStage.TECH: PromptTemplate(
                template="Identify the primary technology type: {context}",
                model="ft:gpt-4-...:tech-classifier",
                validation=lambda x: x in ["solar", "wind", "battery", "multiple"]
            ),
            ProjectStage.COMPONENT: PromptTemplate(
                template="For {tech} technology, identify the specific component: {context}",
                model="ft:gpt-4-...:component-classifier",
                dependencies=[ProjectStage.TECH]
            ),
            ProjectStage.EXPANSION: PromptTemplate(
                template="How many expansion phases are mentioned: {context}",
                model="ft:gpt-4-...:expansion-counter",
                validation=lambda x: isinstance(int(x), int) and int(x) > 0
            )
        }
        self.results = {}

    async def execute_chain(self, context: str) -> Dict[str, Any]:
        """Execute the prompt chain in the correct order, respecting dependencies."""
        
        # Start with stages that have no dependencies
        for stage in ProjectStage:
            if not self.prompts[stage].dependencies:
                self.results[stage] = await self._execute_prompt(stage, context)

        # Then process stages with dependencies
        for stage in ProjectStage:
            if self.prompts[stage].dependencies:
                # Check if dependencies are met
                if all(dep in self.results for dep in self.prompts[stage].dependencies):
                    self.results[stage] = await self._execute_prompt(stage, context)

        return self.results

    async def _execute_prompt(self, stage: ProjectStage, context: str) -> Any:
        prompt = self.prompts[stage]
        
        # Format prompt with context and any dependent results
        formatted_context = context
        if prompt.dependencies:
            formatted_context = context + "\n" + "\n".join(
                f"{dep.value}: {self.results[dep]}"
                for dep in prompt.dependencies
            )

        result = await self._call_api(
            prompt.template.format(context=formatted_context),
            prompt.model
        )

        # Validate result if validation function exists
        if prompt.validation and not prompt.validation(result):
            raise ValueError(f"Invalid result for {stage}: {result}")

        return result

    async def _call_api(self, prompt: str, model: str) -> str:
        # Implementation of API call here
        pass 