from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="steamcontroller-haptics",
    version="1.0.0",
    author="WinCurl Developer",
    author_email="developer@example.com",
    description="Cross-platform, kernel-friendly haptic feedback library for Steam Controllers (Original & 2026 IBEX)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wincurl/steamcontroller-haptics",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Topic :: Games/Entertainment",
        "Topic :: System :: Hardware",
    ],
    python_requires=">=3.6",
)
