from enum import StrEnum


class PermissionCode(StrEnum):
    roles_create = "roles:create"
    users_assign_role = "users:assign_role"
    users_read = "users:read"
    documents_upload = "documents:upload"
    documents_edit = "documents:edit"
    documents_view = "documents:view"
    documents_search = "documents:search"
    documents_delete = "documents:delete"
    rag_index = "rag:index"
    rag_remove = "rag:remove"
    rag_search = "rag:search"
    rag_context = "rag:context"
