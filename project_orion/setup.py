from setuptools import find_packages, setup

package_name = 'project_orion'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='inspiredkhalid',
    maintainer_email='rasakkhalid145@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'state_manager_node = project_orion.state_manager_node:main',
            'state_monitor_node = project_orion.state_monitor_node:main',
        ],
    },
)
