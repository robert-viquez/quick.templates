from pathlib import Path

from models.template import Template


class TemplateService:
    def __init__(self, base_directory: Path) -> None:
        self.base_directory = base_directory

    def get_templates(self) -> list[Template]:
        if not self.base_directory.exists():
            return []

        templates: list[Template] = []

        for path in self.base_directory.rglob("*.md"):
            try:
                content = path.read_text(encoding="utf-8").strip()
            except (OSError, UnicodeError):
                continue

            templates.append(
                Template(
                    title=path.stem,
                    content=content,
                    path=path,
                    folder=path.parent.name,
                )
            )

        return sorted(
            templates,
            key=lambda template: template.title.casefold(),
        )

    def search_templates(
            self,
            query: str,
            templates: list[Template] | None = None,
        ) -> list[Template]:
            if templates is None:
                templates = self.get_templates()

            normalized_query = query.strip().casefold()

            if not normalized_query:
                return templates

            terms = normalized_query.split()

            def matches(template: Template) -> bool:
                searchable_text = " ".join(
                    [
                        template.title,
                        template.content,
                        template.folder,
                    ]
                ).casefold()

                return all(term in searchable_text for term in terms)

            return [
                template
                for template in templates
                if matches(template)
            ]