from setuptools import setup
setup(
    name='wincurl3',
    version='3.0.29',
    description='WinCurl 3 - A Multiplayer Curling Simulator',
    author='Jason',
    packages=['wincurl3'],
    package_dir={'wincurl3': '.'},
    include_package_data=True,
    install_requires=[
        'pygame-ce>=2.5.0',
    ],
    entry_points={
        'console_scripts': [
            'wincurl3=wincurl3.main:main',
        ],
    },
    python_requires='>=3.8',
)
