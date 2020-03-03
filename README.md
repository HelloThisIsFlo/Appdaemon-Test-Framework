# Appdaemon Test Framework
[![Travis](https://img.shields.io/travis/FlorianKempenich/Appdaemon-Test-Framework.svg)](https://travis-ci.org/FlorianKempenich/Appdaemon-Test-Framework) [![PyPI](https://img.shields.io/pypi/v/appdaemontestframework.svg)](https://pypi.org/project/appdaemontestframework/)

Clean, human-readable tests for your Appdaemon automations.

* Totally transparent, No code modification is needed.
* Mock the state of your home: `given_that.state_of('sensor.temperature').is_set_to('24.9')`
* Seamless assertions: `assert_that('light.bathroom').was.turned_on()`
* Simulate time: `time_travel.fast_forward(2).minutes()`

##### How does it look?
```python
def test_during_night_light_turn_on(given_that, living_room, assert_that):
    given_that.state_of('sensor.living_room_illumination').is_set_to(200) # 200lm == night
    living_room._new_motion(None, None, None)
    assert_that('light.living_room').was.turned_on()

def test_click_light_turn_on_for_5_minutes(given_that, living_room, assert_that):
    living_room._new_button_click(None, None, None)
    assert_that('light.bathroom').was.turned_on()

    # At T=4min light should not yet have been turned off
    time_travel.fast_forward(4).minutes()
    assert_that('light.bathroom').was_not.turned_off()

    # At T=5min light should have been turned off
    time_travel.fast_forward(1).minutes()
    time_travel.assert_current_time(5).minutes()
    assert_that('light.bathroom').was.turned_off()

```

---
## Table of Contents

- [5-Minutes Quick Start Guide](#5-minutes-quick-start-guide)
  * [Initial Setup](#initial-setup)
  * [Write you first unit test](#write-you-first-unit-test)
  * [Result](#result)
- [General Test Flow and Available helpers](#general-test-flow-and-available-helpers)
  * [0. Initialize the automation: `@automation_fixture`](#0-initialize-the-automation-automation_fixture)
  * [1. Set the stage to prepare for the test: `given_that`](#1-set-the-stage-to-prepare-for-the-test-given_that)
  * [2. Trigger action on your automation](#2-trigger-action-on-your-automation)
  * [3. Assert on your way out: `assert_that`](#3-assert-on-your-way-out-assert_that)
  * [Bonus — Assert callbacks were registered during `initialize()`](#bonus--assert-callbacks-were-registered-during-initialize)
  * [Bonus — Travel in Time: `time_travel`](#bonus--travel-in-time-time_travel)
- [Examples](#examples)
- [Under The Hood](#under-the-hood)
- [Advanced Usage](#advanced-usage)
- [Contributing](#contributing)
- [Author Information](#author-information)

---

## 5-Minutes Quick Start Guide
### Initial Setup
1. Install **pytest**: `pip install pytest`
1. Install the **framework**: `pip install appdaemontestframework`
1. Create a `conftest.py` file in the **root** of your project with the following code:
   ```python
   from appdaemontestframework.pytest_conftest import *
   ```

### Write you first unit test
Let's test an Appdaemon automation we created, which, say, handles automatic lighting in the Living Room: `class LivingRoom`
<!-- We called the class `LivingRoom`. Since it's an Appdaemon automation, its lifecycle is handled  -->

1. **Initialize** the Automation Under Test with the `@automation_fixture` decorator:
   ```python
   @automation_fixture(LivingRoom)
   def living_room():
     pass
   ```
1. **Write your first test:**
   ##### Our first unit test
   ```python
   def test_during_night_light_turn_on(given_that, living_room, assert_that):
       given_that.state_of('sensor.living_room_illumination').is_set_to(200) # 200lm == night
       living_room._new_motion(None, None, None)
       assert_that('light.living_room').was.turned_on()
   ```
   > ##### Note
   > The following fixtures are **injected** by pytest using the **[`conftest.py`](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/new-features/doc/full_example/conftest.py) file** and the **initialisation fixture created at Step 1**:
   > * `living_room`
   > * `given_that`
   > * `assert_that`
   > * `time_travel`

### Result
```python
# Important:
# For this example to work, do not forget to copy the `conftest.py` file.

@automation_fixture(LivingRoom)
def living_room():
    pass

def test_during_night_light_turn_on(given_that, living_room, assert_that):
    given_that.state_of('sensor.living_room_illumination').is_set_to(200) # 200lm == night
    living_room._new_motion(None, None, None)
    assert_that('light.living_room').was.turned_on()

def test_during_day_light_DOES_NOT_turn_on(given_that, living_room, assert_that):
    given_that.state_of('sensor.living_room_illumination').is_set_to(1000) # 1000lm == sunlight
    living_room._new_motion(None, None, None)
    assert_that('light.living_room').was_not.turned_on()
```


---
## General Test Flow and Available helpers
### 0. Initialize the automation: `@automation_fixture`
```python
# Command
@automation_fixture(AUTOMATION_CLASS)
def FIXTURE_NAME():
    pass

# Example
@automation_fixture(LivingRoom)
def living_room():
    pass
```
The automation given to the fixture will be:
* **Created**
  _Using the required mocks provided by the framework_
* **Initialized**
  _By calling the `initialize()` function_
* **Made available as an injectable fixture**
   _Just like a regular `@pytest.fixture`_

### 1. Set the stage to prepare for the test: `given_that`
*    #### Simulate args passed via `apps.yaml` config
     See: [Appdaemon - Passing arguments to Apps](http://appdaemon.readthedocs.io/en/latest/APPGUIDE.html#passing-arguments-to-apps)
     ```python
     # Command
     given_that.passed_arg(ARG_KEY).is_set_to(ARG_VAL)

     # Example
     given_that.passed_arg('color').is_set_to('blue')
     ```

     Note: See [Pre-initialization Setup](#pre-initialization-setup) if
     arguments are required in the `initialize()` method.

*    #### State
     ```python
     # Command
     given_that.state_of(ENTITY_ID).is_set_to(STATE_TO_SET)
     given_that.state_of(ENTITY_ID).is_set_to(STATE_TO_SET, ATTRIBUTES_AS_DICT)
     given_that.state_of(ENTITY_ID).is_set_to(STATE_TO_SET,
                                              ATTRIBUTES_AS_DICT,
                                              LAST_UPDATED_AS_DATETIME,
                                              LAST_CHANGED_AS_DATETIME)

     # Example
     given_that.state_of('media_player.speaker').is_set_to('playing')
     given_that.state_of('light.kitchen').is_set_to('on', {'brightness': 50,
                                                           'color_temp': 450})

     given_that.state_of('light.kitchen').is_set_to(
                                            'on', 
                                            last_updated=datetime(2020, 3, 3, 11, 27))
     ```

*    #### Time
     ```python
     # Command
     given_that.time_is(TIME_AS_DATETIME)

     # Example
     given_that.time_is(time(hour=20))
     ```

*    #### Extra
     ```python
     # Clear all calls recorded on the mocks
     given_that.mock_functions_are_cleared()

     # To also clear all mocked state, use the option: 'clear_mock_states'
     given_that.mock_functions_are_cleared(clear_mock_states=True)

     # To also clear all mocked passed args, use the option: 'clear_mock_passed_args'
     given_that.mock_functions_are_cleared(clear_mock_passed_args=True)
     ```

### 2. Trigger action on your automation
The way Automations work in Appdaemon is:
* First you **register callback methods** during the `initialize()` phase
* At some point **Appdaemon will trigger these callbacks**
* Your Automation **reacts to the call on the callback**

To **trigger actions** on your automation, simply **call one of the registered callbacks**.

> #### Note
> It is best-practice to have an initial test that will test the callbacks
> are _actually_ registered as expected during the `initialize()` phase.
> See: [Bonus - Assert callbacks were registered during `initialize()`](#bonus--assert-callbacks-were-registered-during-initialize)

#### Example

##### `LivingRoomTest.py`
```python
def test_during_night_light_turn_on(given_that, living_room, assert_that):
   ...
   living_room._new_motion(None, None, None)
   ...
```

##### With `LivingRoom.py`
```python
class LivingRoom(hass.Hass):
    def initialize(self):
        ...
        self.listen_event(
                self._new_motion,
                'motion',
                entity_id='binary_sensor.bathroom_motion')
        ...

    def _new_motion(self, event_name, data, kwargs):
        < Handle motion here >
```



### 3. Assert on your way out: `assert_that`

*    #### Entities
     ```python
     # Available commmands
     assert_that(ENTITY_ID).was.turned_on(OPTIONAL_KWARGS)
     assert_that(ENTITY_ID).was.turned_off(OPTIONAL_KWARGS)
     assert_that(ENTITY_ID).was_not.turned_on(OPTIONAL_KWARGS)
     assert_that(ENTITY_ID).was_not.turned_off(OPTIONAL_KWARGS)

     # Examples
     assert_that('light.living_room').was.turned_on()
     assert_that('light.living_room').was.turned_on(color_name=SHOWER_COLOR)
     assert_that('light.living_room').was_not.turned_off()
     assert_that('light.living_room').was_not.turned_off(transition=2)
     ```

*    #### Services
     ```python
     # Available commmands
     assert_that(SERVICE).was.called_with(OPTIONAL_KWARGS)
     assert_that(SERVICE).was_not.called_with(OPTIONAL_KWARGS)

     # Examples
     assert_that('notify/pushbullet').was.called_with(
                         message='Hello :)',
                         target='My Phone')

     assert_that('media_player/volume_set').was.called_with(
                         entity_id='media_player.bathroom_speaker',
                         volume_level=0.6)
     ```


### Bonus — Assert callbacks were registered during `initialize()`
*    #### Listen: Event
     ```python
     # Available commmands
     assert_that(AUTOMATION) \
         .listens_to.event(EVENT) \
         .with_callback(CALLBACK)
     assert_that(AUTOMATION) \
         .listens_to.event(EVENT, OPTIONAL_KWARGS) \
         .with_callback(CALLBACK)

     # Examples - Where 'living_room' is an instance of 'LivingRoom' automation
     assert_that(living_room) \
         .listens_to.event('click', entity_id='binary_sensor.button') \
         .with_callback(living_room._new_click_button)
     ```

*    #### Listen: State
     ```python
     # Available commmands
     assert_that(AUTOMATION) \
         .listens_to.state(ENTITY_ID) \
         .with_callback(CALLBACK)
     assert_that(AUTOMATION) \
         .listens_to.state(ENTITY_ID, OPTIONAL_KWARGS) \
         .with_callback(CALLBACK)

     # Examples - Where 'living_room' is an instance of 'LivingRoom' automation
     assert_that(living_room) \
         .listens_to.state('binary_sensor.button', old='on', new='off') \
         .with_callback(living_room._no_more_motion)
     ```

*    #### Registered: Run Daily
     ```python
     # Available commmands
     assert_that(AUTOMATION) \
         .registered.run_daily(TIME_AS_DATETIME) \
         .with_callback(CALLBACK)
     assert_that(AUTOMATION) \
         .registered.run_daily(TIME_AS_DATETIME, OPTIONAL_KWARGS) \
         .with_callback(CALLBACK)

     # Examples - Where 'living_room' is an instance of 'LivingRoom' automation
     assert_that(living_room) \
         .registered.run_daily(time(hour=12), time_as_text='noon') \
         .with_callback(automation._new_time)
     ```

     **NOTE:** The above examples can be used with run_minutely.

_See related test file for more examples: [test_assert_callback_registration.py](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/master/test/test_assert_callback_registration.py)_


### Bonus — Travel in Time: `time_travel`
This helper simulate going forward in time.

It will run the callbacks registered with the `run_in`function of Appdaemon:
* **Order** is kept
* Callback is run **only if due** at current simulated time
* **Multiples calls** can be made in the same test
* Automatically **resets between each test** _(with default config)_


 ```python
# Available commmands

## Simulate time
time_travel.fast_forward(MINUTES).minutes()
time_travel.fast_forward(SECONDS).seconds()

## Assert time in test — Only useful for sanity check
time_travel.assert_current_time(MINUTES).minutes()
time_travel.assert_current_time(SECONDS).seconds()



# Example

# 2 services:
#   * 'first/service': Should be called at T=3min
#   * 'second/service': Should be called at T=5min
time_travel.assert_current_time(0).minutes()

time_travel.fast_forward(3).minutes()
assert_that('some/service').was.called()
assert_that('some_other/service').was_not.called()

time_travel.fast_forward(2).minutes()
assert_that('some_other/service').was.called()
```

---
## Examples
### Simple
*  [**Pytest**](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/master/doc/pytest_example.py)
*  [**Unittest**](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/master/doc/unittest_example.py)

### Special cases
#### Complex setup fixture
In this scenario, we wish to test what happens **after** the light was turned on by motion and the `device_tracker.person` is set to `away`.
After the first `_new_motion`, the mock functions must be reset to ensure a clean state. For that purpose, it is entirely possible to use `given_that.mock_functions_are_cleared()` inside a particular test:
```python
def test_light_turned_on_by_motion_and_person_away__do_not_turn_on_again(given_that,
                                                                         living_room,
                                                                         assert_that):
  # Given:
  # - Light was turned on by motion
  given_that.state_of('sensor.living_room_illumination').is_set_to(200) # 200lm == night
  living_room._new_motion(None, None, None)
  given_that.mock_functions_are_cleared()
  # - Person is away
  given_that.state_of('device_tracker.person).is_set_to('away')


  # When: New motion
  living_room._new_motion(None, None, None)


  # Then: Light isn't turned on
  assert_that('light.living_room').was_not.turned_on()
```

Alternatively, if multiple scenarios are to be tested with the same fixture (after turned on by motion & person is away), an intermediate fixture can be used:

```python
class AfterLightTurnedOnByMotion:

  @pytest.fixture
  def living_room_after_light_turned_on_by_motion(self, living_room, given_that):
    given_that.state_of('sensor.living_room_illumination').is_set_to(200) # 200lm == night
    living_room._new_motion(None, None, None)
    given_that.mock_functions_are_cleared()

  def test_person_away__new_motion__do_not_turn_on_again(self,
                                                         given_that,
                                                         living_room_after_light_turned_on_by_motion,
                                                         assert_that):
    given_that.state_of('device_tracker.person).is_set_to('away')
    living_room_after_light_turned_on_by_motion._new_motion(None, None, None)
    assert_that('light.living_room').was_not.turned_on()

  def test_some_other_condition__do_something_else(self,
                                                   given_that,
                                                   living_room_after_light_turned_on_by_motion,
                                                   assert_that):
    ...

```


### [Complete Project](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/tree/master/doc/full_example)
* **Kitchen**
  * [**Automation**](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/master/doc/full_example/apps/kitchen.py)
  * [**Tests**](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/master/doc/full_example/tests/test_kitchen.py)
* **Bathroom**
  * [**Automation**](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/master/doc/full_example/apps/bathroom.py)
  * [**Tests**](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/master/doc/full_example/tests/test_bathroom.py)

---

## Under The Hood
> This section is **entirely optional**
> For a guide on how to use the framework, see the above sections!

### Understand the motivation
**Why a test framework dedicated for Appdaemon?**
_The way Appdaemon allow the user to implement automations is based on inheritance.
This makes testing not so trivial.
This test framework abstracts away all that complexity, allowing for a smooth TDD experience._

**Couldn't we just use the MVP pattern with clear interfaces at the boundaries?**
_Yes we could... but would we?
Let's be pragmatic, with this kind of project we're developing for our home, and we're a team of one.
While being a huge proponent for [clean architecture](https://floriankempenich.com/post/11), I believe using such a complex architecture for such a simple project would only result in bringing more complexity than necessary._

### Enjoy the simplicity

Every Automation in Appdaemon follows the same model:
* **Inherit** from **`hass.Hass`**
* **Call** Appdaemon API through **`self`**

**AppdaemonTestFramework** captures all calls to the API and helpers make use of the information to implement common functionality needed in our tests.

Methods from the `hass.Hass` class are patched globally in the `HassMocks` class and the mocks can be accessed with the `hass_functions` property. The test fixture is injected in the helper classes as `hass_mocks`.
After all tests have run, the `hass_mocks` test fixture will automatically unpatch all the mocks.

> **Deprecated `hass_functions` test fixture**
> Before `HassMocks` existed, `hass_functions` was used for interacting with the patch hass methods. The `hass_mocks` test fixture now contains `hass_functions` and should be accessed through there.
> A `hass_functions` test fixture that returns `hass_mocus.hass_fuctions` will be kept for a while to ease transition, but wil generate a deprecation warning.

1. **`hass_functions`**: **dictionary** with all patched functions
1. **`unpatch_callback`**: **callback** to un-patch all patched functions

**`hass_functions`** are injected in the helpers when creating their instances.
After all tests, **`unpatch_callback`** is used to un-patch all patched functions.

Setup and teardown are handled in the [`pytest_conftest.py`](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/master/appdaemontestframework/pytest_conftest.py) file.


#### Appdaemon Test Framework flow
###### 1. Setup
* **Patch** `hass.Hass` functions and create `HassMocks` instance for tracking state.
* **Inject** `hass_mocks` in helpers: `given_that`, `assert_that`, `time_travel`
###### 2. Test run
* **Run** the test suite
###### 3. Teardown
* **Un-patch** `hass.Hass` functions

### Feature focus
#### `@automation_fixture`

To be able to test an Appdaemon automation, the automation needs to be created **after** the framework has been
initialized. This could be done with a regular `@pytest.fixture` by injecting `given_that` (or any other helper) before
creating the automation. This would invoke the helper which would initialize the framework beforehand and the correct
functions would be patched before the automation is created:
```python
@pytest.fixture
def living_room(given_that):
    # `None` dependencies are mocked by the framework
    living_room = LivingRoom(None, None, None, None, None, None, None, None)
    return living_room
```

Also, for convenience, we could initialize the automation with its `initialize()` method to make it available in tests
as it would be in production once Appdaemon is started, making sure the mocks are clear of any calls when the fixture
is injected. We could also set the automation instance name to the name of the automation class.
```python
@pytest.fixture
def living_room(given_that):
    living_room = LivingRoom(None, LivingRoom.__name__, None, None, None, None, None, None)
    living_room.initialize()
    given_that.mock_functions_are_cleared()
    return living_room
```

However, since this code would have to be repeated for every single automation, it was creating un-necessary clutter.
For that reason, the `@automation_fixture` was introduced. It is simple syntactic sugar, and performs the exact same
steps as the fixture above in much fewer lines:

```python
@automation_fixture(LivingRoom)
def living_room():
    pass
```


## Advanced Usage

### `@automation_fixture` - Extra features
* #### Pre-initialization setup
  For some automations, the `initialize()` step requires some pre-configuration of the global state.
  Maybe it requires time to be setup, or maybe it needs some sensors to have a particular state.
  Such pre-initialization setup is possible with the `@automation_fixture`. The fixture can be injected with the
  following 2 arguments:
  * `given_that` _- For configuring the state_
  * `hass_mocks` _- For more complex setup steps_
    * Note: `hass_functions` was deprecated in favor of using `hass_mocks`

  Any code written in the fixture will be executed **before** initializing the automation. That way your
  `initialize()` function can safely rely on the Appdaemon framework and call some of its methods, all you
  have to do is setup the context in the fixture.

  ##### Example
  Let's imagine an automation, `Terasse`, that turns on the light at night. During the `initialize()` phase, `Terasse`
  checks the current time to know if it should immediately turn on the light (for instance, if appdaemon is started
  during the night).
  Without mocking the time **before** the call to `initialize()` the test framework will not know which time to return
  and an error will be raised. To prevent that, we set the time in the fixture, the code will be executed **before** the
  call to `initialize()` and no error will be raised.
  ```python
  @automation_fixture
  def terasse(given_that):
      given_that.time_is(datetime.time(hour=20))


  # With Terasse:
  class Terasse(hass.Hass):
      def initialize(self):
          ...
          current_time = self.time()
          if self._is_during_night(current_time):
              self._turn_on_light()
          ...
  ```

* #### Alternate versions
  The `@automation_fixture` can actually be used in 4 different ways:
  ```python
  # Single Class:
  @automation_fixture(MyAutomation)

  # Multiple Classes:
  @automation_fixture(MyAutomation, MyOtherAutomation)

  # Single Class w/ params:
  @automation_fixture((upstairs.Bedroom, {'motion': 'binary_sensor.bedroom_motion'}))

  # Multiple Classes w/ params:
  @automation_fixture(
    (upstairs.Bedroom, {'motion': 'binary_sensor.bedroom_motion'}),
    (upstairs.Bathroom, {'motion': 'binary_sensor.bathroom_motion'}),
  )
  ```

  The alternate versions can be useful for parametrized testing:
  * When multiple classes are passed, tests will be generated for each automation.
  * When using parameters, the injected object will be a tuple: `(Initialized_Automation, params)`

### Deprecation Warnings
As development continues of this test framework, some interfaces and test fixtures need to get
deprecated. In general, the following method is used to ease the transitions

1. Mark deprecated calls with a warning
1. Provide an expressive message directing you how to change your code
1. At least one minor release will include the warning
1. In a future MAJOR release, this warning will change to an error and/or the deprecated code will be
   removed all together.

This deprecation strategy allows you to keep using Appdaemon Test Framework as you always have, as long as you don't update to a new MAJOR version.


**Silencing deprecation warnings**

The deprecation warnings can be a bit overwhelming depending on the current state of the codebase.
If you would like to run tests and ignore these warnings use the following pytest options:

```sh
pytest -W ignore::DeprecationWarning
```

### Without `pytest`
If you do no wish to use `pytest`, first maybe reconsider, `pytest` is awesome :)
If you're really set on using something else, worry not it's pretty straighforward too ;)

What the [`conftest.py`](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/new-features/doc/full_example/conftest.py) file is doing is simply handling the setup & teardown, as well as providing the helpers as injectable fixtures.
It is pretty easy to replicate the same behavior with your test framework of choice. For instance, with `unittest` a base `TestCase` can replace pytest [`conftest.py`](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/new-features/doc/full_example/conftest.py). See the [Unittest Example](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/master/doc/unittest_example.py)

### Direct call to mocked functions
> /!\ WARNING — EXPERIMENTAL /!\

**Want a functionality not implemented by the helpers?**
You can inject `hass_mocks` directly in your tests and use `hass_mocks.hass_functions`, patched functions are `MagicMocks`.
The list of patched functions can be found in the [**`hass_mocks` module**](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/master/appdaemontestframework/hass_mocks.py#L20framework.py#L14).


---
## Contributing

* **All contributions are welcome!**
* **All PR must be accompanied with some tests showcasing the new feature**
* **For new feature, a short discussion will take place to argue whether the feature makes sense and if this is the best place to implement**

* **Then the process goes as follow:**
  * Is readable? ✅
  * Passes the tests? ✅
  * I'm merging 🎉🎉


> PR simply patching new functions in `hass_functions`
>   * Will be merged almost immediately
>   * Are exempt of the _"must have tests"_ rule, although there is rarely too much tests 😉

Thanks for your contribution 😀 👍


### Tests

When adding new feature, you can TDD it, add unit tests later, or only rely on integration tests. Whichever way you go is totally fine for this project, but new features will need to have at least some sort of tests, even if they're super basic 🙂

### Using `Pipenv`
This project has been developed using `Pipenv`.
It is totally optional, but if you are interested, here is a quick guide to get you started:
1. Install `pipenv` -> `brew install pipenv` (or whichever methods works best for you)
2. `cd` in the project directory
3. Run `pipenv install --dev`  
  _That will create a `virtualenv` and automatically install all required dependencies_
4. Run `pipenv shell`  
  _That will activate the `virtualenv` in the current shell_
5. Run `pytest` to ensure that everything is working as expected
6. You're good to go and can start contributing 😊

---
## Author Information
Follow me on Twitter: [@ThisIsFlorianK](https://twitter.com/ThisIsFlorianK)
Find out more about my work: [Florian Kempenich — Personal Website](https://floriankempenich.com)
