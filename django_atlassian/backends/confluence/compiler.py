# -*- coding: utf-8 -*-


from django_atlassian.backends.common import compiler

class SQLCompiler(compiler.SQLCompiler):
    query_param = 'cql'
