from setuptools import setup, find_packages

setup(
    name='appdaemontestframework',
    version='4.0.0b2',
    description='Clean, human-readable tests for Appdaemon',
    long_description='See: https://floriankempenich.github.io/Appdaemon-Test-Framework/',
    keywords='appdaemon homeassistant test tdd clean-code home-automation',
    classifiers=[
        'Environment :: Console',
        'Framework :: Pytest',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Utilities',
        'Topic :: Home Automation',
        'Topic :: Software Development :: Testing'
    ],
    url='https://floriankempenich.github.io/Appdaemon-Test-Framework',
    author='Florian Kempenich',
    author_email='Flori@nKempenich.com',
    packages=find_packages(),
    license='MIT',
    python_requires=">=3.7",
    install_requires=[
        'appdaemon>=4.0,<5.0',
        'mock>=3.0.5,<4.0',
        'packaging>=20.1,<21.0',
    ],
    include_package_data=True
)
