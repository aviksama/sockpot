from setuptools import setup

setup(
    name="sockpot",
    version="0.1a0",
    author='Avik',
    author_email="eml2avik@gmail.com",
    packages=['sockpot', 'sockpot/conf'],
    description="Multithreaded tcp based socket server and client",
    install_requires=['gevent>=1.2', 'six>=1.1'],
    entry_points={
        "console_scripts": [
            "sockpot_serve=sockpot.run:serve"]
    },
    python_requires='>=2.7'
)