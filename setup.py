from setuptools import setup, find_packages

setup(
    name="tourman",
    version="1.0.0",
    description="Tournament management CLI tool",
    author="Sadi Mamedov",
    author_email="sadimamedov7@gmail.com",
    packages=find_packages(where="src"),
    py_modules=["main"],
    package_dir={"": "src"},
    include_package_data=True,
    package_data={
        "db": ["*.sql"],          # bundle SQL files
    },
    install_requires=[
        "psycopg2-binary",
        "pandas",
        "openpyxl",
        "Faker",
        "Jinja2",
    ],
    entry_points={
        "console_scripts": [
            "tourman = main:main",
        ],
    },
    extras_require={
        "test": [
            "pytest>=7.0",
            "pytest-order",
        ],
    },
    python_requires=">=3.8",
)