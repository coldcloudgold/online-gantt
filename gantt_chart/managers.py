from typing import TYPE_CHECKING

from django.db.models import Manager, QuerySet

if TYPE_CHECKING:
    from gantt_chart.models import ProjectParticipant, ProjectRole


class ProjectParticipantRoleManager(Manager):
    def update_role_for_participant(self, participant: "ProjectParticipant", roles: QuerySet["ProjectRole"]):
        if not self.filter(participant=participant).exists():
            self.bulk_create([self.model(participant=participant, role=role) for role in roles])
            return

        all_roles_id = set(self.filter(participant=participant).values_list("role", flat=True))
        roles_id = set(roles.values_list("id", flat=True))
        if all_roles_id != roles_id:  # Если идентификаторы ролей не совпадают
            # Роли подлежащие удалению
            roles_to_remove_id = all_roles_id - roles_id
            if roles_to_remove_id:
                self.model.objects.filter(participant=participant, role__in=roles_to_remove_id).delete()
            # Роли подлежащие созданию
            roles_to_create_id = roles_id - all_roles_id
            if roles_to_create_id:
                from gantt_chart.models import ProjectRole

                roles_to_create = ProjectRole.objects.filter(id__in=roles_to_create_id)
                self.bulk_create([self.model(participant=participant, role=role) for role in roles_to_create])
