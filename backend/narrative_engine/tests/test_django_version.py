import django


def test_the_project_runs_on_django_6_1():
    assert django.VERSION[:2] == (6, 1)
