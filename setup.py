from setuptools import setup, find_packages

setup(
    name='generate-kulturens-lists',
    use_scm_version=True,
    packages=find_packages(),
    setup_requires=[
        'setuptools_scm'
    ],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        generate_kulturens_lists=generate_kulturens_lists.cli:cli
    ''',
)