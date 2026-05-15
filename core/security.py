def register_security_headers(app):
    """Cabeçalhos seguros sem alterar o front-end.

    Não adiciona CSP rígida para não quebrar scripts/estilos existentes. A CSP
    pode ser ativada depois de mapear todos os assets inline.
    """
    @app.after_request
    def add_headers(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        return response
