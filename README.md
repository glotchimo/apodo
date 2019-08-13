# Gato
The async Python web framework that acts fast and lands on its feet.

Gato is an asynchronous Python web framework that derives from the Vibora framework, implementing Cython and other performance-enhancing technologies to significantly increase processing speed and efficiency.

## Framework Goals
- Go quick
- Run clean
- Stay simple

## Project Goals
- Work together
- Generate and support cool ideas
- Learn and grow as a team

"Your team's strength is not a function of the talent of individual members. It's a function of their collaboration, tenacity, and mutual respect."

## Development Plan
Gato, while derived from the Vibora framework, will be built with a new design philosophy in mind. We will reference the old source of Vibora as we build, but only for some lower-level concepts.

A major pitfall of Vibora was its lack of strict system design guidelines, as well of its lack of documentation. Solid design is to be held in high regard along with functional speed, and design should not and will not be compromised for functional speed. Building a spaghetti dinner that runs very quickly is fine, but building a well-designed, fast, and scalable web framework is what we're more interested in.

The plan for Gato is to start with base functionality, and iteratively add features, with Vibora as a functional reference.

## Development Pipeline

As one of our goals is to work together, the development pipeline is structured knowing that all may not be comfortable/confident enough with Cython and lower-level concepts to be able to contribute to the core system.

### Vibora Analysis
This project is for those mentioned above. As the core team works, it is necessary that we are able to reference Vibora. Vibora is woefully lacking in its inline and online documentation, and a way for newcomers to contribute is by digging through the source in the `legacy` package, figuring out what it does, and writing in docstrings/refactoring illegible code. This process will not only support and speed up the development of Gato, but also equip newcomers with tons of knowledge about how this type of web framework operates under the hood.

To contribute in this way, all you have to do is fork with the branch schema of `v-rewrite-<module or package name>` and submit a PR once you're done adding docstrings and refactoring illegible code. Your PR must pass one review before it is merged to `dev`.

### Core Development
This project is for those experienced in Python, with knowledge of how it works as a language, as well as C concepts like Cython and other C-optimised practices and libraries, as well as sufficient understanding of web technologies and practices.

In order to contribute this way, you must be in the Gato Slack group and approved as a contributor on the core repository.

Contribution to the core system will be heavily discussion-based until we release a first iteration, after which the iterative feature adds will begin. Until then, contact Elliott about joining the core team, and we'll go from there.

## Development Guidelines

Be aware that we utilize git hooks to automate and standardize some of the development process. We will conform to our written configurations of the `black` formatter, and of the `flake8` linter.

### Comments/docstrings

As it stands, commenting and style consistency is woefully lacking in the Vibora library, and those are two things being addressed in this port before we begin work on features/fixes. We will use `black` for formatting, and comment styling will be as follows.

For module docstrings, comments should look like this:

    """
    gato.utils.module (modular path)
    ~~~~~~~~~~~~~~~~~

    This module implements the `Class` class, and other stuff. (module description)
    """

For class docstrings, comments should look like this:

    """ Implements the `Class` class. (short description)

    This class does things that it does. We've written it to do
    actions and carry out tasks. (long description)

    :param `*args`: These are some arguments.
    :param `**kwargs`: These are some keyword arguments. (parameters)
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

#### Soft Rules:
- Put backticks (``) around object and variable names.
- Wrap comments to 88 characters.
- Capitalize the first letters of parameter and return descriptions.

### Typing

We will *not* use type hints. While helpful to an extent, type hints in Python dirty code significantly, and typing can be notated in docstrings. So, the parameter and return lines in all method docstrings MUST denote the intended type of the given variables.

## Let's build together.
The Vibora framework, while intelligently conceptualized and designed, lacked the community and structure that an open-source project needs to thrive. While a lot of brilliant engineers have created great open-source software mostly on their own, it's more meaningful and enriching for all involved when it becomes a community effort.

A major goal of this project is to cultivate an efficient and involved development/contribution pipeline, rather than an isolated and centralized dependent workflow for few.

This project needs developers! Join us on the [slack channel](https://join.slack.com/t/gatoproject/shared_invite/enQtNzA1NjcwMDU4MDA2LWIyZWFmNDY2YzEyM2RmYWQ2OWM3MzQyN2QwYzllYzg3OGRhMzJkOWIwMjA2OTEyOGVkYTliZTA4OWQwMDI1Y2U)
