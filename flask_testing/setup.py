from setuptools import setup

setup(
    name='ccssrg',
    packages=['ccssrg'],
    include_package_data=True,
    install_requires=[
        'flask',
        'pytz',
        'canvasapi'
    ],
)