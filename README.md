# Gato
The async Python web framework that acts fast and lands on its feet.

Gato is an asynchronous Python web framework that models the Vibora framework, implementing Cython and other performance-enhancing technologies to significantly increase processing speed and efficiency.

## Goals
- Go quick
- Run clean
- Stay simple

## Development Plan
Gato is going to be loosely derived from the design goals of the Vibora framework, and to execute this, we will port source from a legacy package of Vibora module-by-module, redesigning as we go.

The first phase of alpha development will be the porting of the entire Vibora library into Gato. This will not simply be a copy-paste job; the goal of this process is to clean and optimize the modules that are coming over to make the future of development simpler and easier.

All port changes will be commited to a development branch, and once the entire port is complete, then development will be merged onto master. After this has been completed, development merges to master will occur on a release basis.

Another thing to note is that, until the entire port is complete, there will be no need or application for tests, as we will not have a complete library to work with, and many modules will have missing first-party dependencies.

Once all source has been ported over, we will begin the testing/monitoring and fixing processes. There are a few major bottlenecks and design flaws that will be addressed once things are running smoothly. Those targets will be finalized once the port is complete.

## Development Pipeline

Pipeline will look slightly different from phase one to phase two.

### Phase one process

1. Create an issue for the module you're porting. Tag the issue with `port`, and it will automatically be added to the port project board.
2. Study the module, write it over piece-by-piece, with style and commenting guidelines in mind, and create a PR attached to your issue.
3. Your PR will be reviewed by the core team, and merged.

Some things to note:

- Module functionality doesn't need to and shouldn't always be altered. The changes that are made in the port should be to commenting, style, and syntax. Major functionality changes will be carried out after the port is complete.
- While you should avoid doing so, if you change module, class, method, or variable names, you MUST propagate those changes through other files.

### Phase two+ process (standard post-port development procedure)

1. Create/address an issue. Name your branch in the format of `port-<module name>`.
2. Implement a fix, and open a PR. Your PR must pass all existing tests, as well as coverage for new code.
3. Receive at least one review from any contributor, and merge.

Contributions to major projects will be tagged accordingly and tracked automatically on project boards.

## Development Guidelines

First of all, be aware that we will utilize git hooks to automate and standardize some of the development process. Right now, the existing hook script is on `pre-commit`, and formats the code with black, and checks it with flake8.

### Comments/docstrings

As it stands, commenting and style consistency is woefully lacking in the Vibora library, and those are two things being addressed in this port before we begin work on features/fixes. We will use out-of-the-box `black` for formatting, and comment styling will be as follows.

For module docstrings, comments should look like this:

    """
    gato.utils.module (modular path)
    ~~~~~~~~~~~~~~~~~

    This module implements the implementation of a module. (module description)
    """

For class docstrings, comments should look like this:

    """ Implements its class. (short description)

    This class does things that it does. We've written it to do
    actions and carry out tasks. (long description)

    :param `*args`: arguments.
    :param `**kwargs`: keyword arguments. (parameters)
    """

For method docstrings, comments should look like this:

    """ Does an action. (short description)

    This method does things and stuff. Note that it does things
    in a certain way as of version 0.1.0. (long description)

    :param `thing`: A thing (`str`) with which to do stuff.
    :param `stuff`: (optional) Some stuff (`dict`) with which to do things. (parameters w/ type intentions)

    :return `product`: A `Product` object. (return w/ type intention)
    """

Other one-line commenting should be kept to a mininum but used effectively and concisely when necessary.

Note that parameter names and object names go in backticks (``) to increase readability in text editors. This is a soft rule.

### Typing

We will *not* use type hints. While helpful to an extent, type hints in Python dirty code significantly, and typing can be notated in docstrings. So, the parameter and return lines in all method docstrings MUST denote the intended type of the given variables.

## Let's build together.
The Vibora framework, while intelligently conceptualized and designed, lacked the community and structure that an open-source project needs to thrive. While a lot of brilliant engineers have created great open-source software mostly on their own, it's more meaningful and enriching for all involved when it becomes a community effort.

A major goal of this project is to cultivate an efficient and involved development/contribution pipeline, rather than an isolated and centralized dependent workflow for few.

This project is brand new and still in the planning phase. Join us on the [slack channel](https://join.slack.com/t/gatoproject/shared_invite/enQtNzA1NjcwMDU4MDA2LWIyZWFmNDY2YzEyM2RmYWQ2OWM3MzQyN2QwYzllYzg3OGRhMzJkOWIwMjA2OTEyOGVkYTliZTA4OWQwMDI1Y2U) to get involved in the decision-making process as we work through the details.
