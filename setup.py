from setuptools import setup, find_packages

setup(
    name='pymatuning',
    version='0.1',
    author="Samuel D. Lotz",
    author_email="samuel.lotz@salotz.info",
    description="Small python library and CLI for generating todos from python modules",
    py_modules=['pymatuning'],
    url="https://github.com/salotz/pymatuning",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'networkx>=2'
    ],
    entry_points={
        'console_scripts' : [
            "pymatuning = pymatuning.cli:cli"]}

)
