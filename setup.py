import os

from setuptools import find_packages, setup

package_name = "publish_anything_ros2_gui"
share_path = "share/" + package_name


setup(
    name=package_name,
    version="1.0.0",
    packages=find_packages(),
    data_files=[
        (share_path, ["package.xml"]),
        (
            os.path.join(share_path, "config"),
            [
                os.path.join("config", "publish_anything_example.yaml"),
                os.path.join("config", "qt_style.qss"),
            ],
        ),
        (
            os.path.join(share_path, "launch"),
            [os.path.join("launch", "publish_anything_ros2_gui_launch.py")],
        ),
        (
            os.path.join("share", "ament_index", "resource_index", "packages"),
            [os.path.join("resource", package_name)],
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    author="Lihan Chen",
    author_email="lihanchen2004@163.com",
    maintainer="Lihan Chen",
    maintainer_email="lihanchen2004@163.com",
    url="https://github.com/ros-teleop/teleop_tools",
    keywords=["ROS"],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache-2.0",
        "Programming Language :: Python",
        "Topic :: Software Development",
    ],
    description="A GUI tool for publishing ROS2 messages using PyQt5.",
    long_description="""\
        This tool provides a graphical user interface (GUI) for publishing ROS2 messages.
        It allows users to configure and publish messages to various ROS2 topics using PyQt5 widgets.
        Users can set message fields, adjust publishing frequency, and start/stop publishing with ease.
        The tool supports nested message types and provides a flexible interface for different message configurations.
    """,
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "publish_anything_ros2_gui = publish_anything_ros2_gui.publish_anything_ros2_gui:main",
        ],
    },
)
