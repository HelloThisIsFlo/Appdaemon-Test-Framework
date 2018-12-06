from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='appdaemontestframework',
    version='1.2.3',
    description='Clean, human-readable tests for Appdaemon',
    long_description=readme(),
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
    packages=['appdaemontestframework'],
    license='MIT',
    install_requires=[
        'appdaemon',
        'mock'
    ],
    include_package_data=True
)
