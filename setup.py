from setuptools import setup

setup(
    name='appdaemontestframework',
    version='2.5.1',
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
    packages=['appdaemontestframework'],
    license='MIT',
    install_requires=[
        'appdaemon',
        'mock'
    ],
    include_package_data=True
)
