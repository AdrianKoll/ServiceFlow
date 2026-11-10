# Constantes centralizadas de tradução, perfis e permissões.
STATUS_PT = {
    'pending': 'Pendente', 'in_progress': 'Em Andamento',
    'completed': 'Concluído', 'cancelled': 'Cancelado',
    'todo': 'A Fazer', 'review': 'Revisão', 'done': 'Concluído',
    'active': 'Ativo', 'inactive': 'Inativo', 'prospect': 'Prospect',
    'paid': 'Pago', 'overdue': 'Atrasado',
}
PRIORITY_PT    = {'low': 'Baixa', 'medium': 'Média', 'high': 'Alta'}
ROLE_PT        = {
    'admin': 'Administrador', 'manager': 'Gerente',
    'technician': 'Técnico', 'sales': 'Vendas', 'client': 'Cliente',
}
EMPLOYEE_ROLES = ['admin', 'manager', 'technician', 'sales']
EVENT_TYPE_PT  = {
    'meeting': 'Reunião', 'visit': 'Visita',
    'deadline': 'Prazo', 'reminder': 'Lembrete', 'other': 'Outro',
}
ROLE_ICON = {
    'admin': '👑', 'manager': '🏢', 'technician': '🔧', 'sales': '💼', 'client': '👤',
}
ROLE_ACCESS = {
    'admin':      '*',
    'manager':    {'dashboard', 'servicos', 'tarefas', 'agenda', 'clientes',
                   'equipe', 'financeiro', 'relatorios', 'desempenho', 'mensagens', 'configuracoes'},
    'technician': {'dashboard', 'servicos', 'tarefas', 'agenda', 'mensagens', 'configuracoes'},
    'sales':      {'dashboard', 'servicos', 'clientes', 'financeiro', 'mensagens', 'configuracoes'},
    'client':     {'portal'},
}
ROLE_LABELS = {
    'admin': 'Administrador', 'manager': 'Gerente', 'technician': 'Técnico',
    'sales': 'Comercial', 'client': 'Cliente',
}
ROLE_ABBR = {'admin': 'AD', 'manager': 'GE', 'technician': 'TE', 'sales': 'CO', 'client': 'CL'}
