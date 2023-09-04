import platform
from setuptools import setup
from setuptools import find_packages


with open('requirements.txt', 'r') as f:
    requirements = f.read()


setup(
    name='piedatalake',
    version='1.0.6',
    python_requires=f'>=3.6',
    description='Datalake search engine',
    url='https://github.com/PieDataLabs/datalake',
    author='George Kasparyants',
    author_email='gg@piedata.ai',
    license='',
    packages=find_packages(include=['datalake', 'datalake.*']),
    install_requires=requirements,
    zip_safe=True,
    include_package_data=True,
    platforms=[platform.platform()],
    classifiers=[
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6"
    ],
    scripts=["scripts/datalaker"]
)
