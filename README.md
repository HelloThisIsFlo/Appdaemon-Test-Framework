# Appdaemon Test Framework
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
  * [1. Set the stage to prepare for the test: `given_that`](#1-set-the-stage-to-prepare-for-the-test-given_that)
  * [2. Trigger action on your automation](#2-trigger-action-on-your-automation)
  * [3. Assert on your way out: `assert_that`](#3-assert-on-your-way-out-assert_that)
  * [Bonus — Travel in Time: `time_travel`](#bonus--travel-in-time-time_travel)
- [Examples](#examples)
- [Under The Hood](#under-the-hood)
- [Advanced Usage](#advanced-usage)
- [Author Information](#author-information)

---

## 5-Minutes Quick Start Guide
### Initial Setup
1. Install **pytest**: `pip install pytest`
1. Install the **framework**: `pip install appdaemontestframework`
1. Copy [**`conftest.py`**](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/master/conftest.py) at the **root** of your project

### Write you first unit test
Let's test an Appdaemon automation we created, which, say, handles automatic lighting in the Living Room: `class LivingRoom`  
<!-- We called the class `LivingRoom`. Since it's an Appdaemon automation, its lifecycle is handled  -->

1. **Initialize** the Automation Under Test in a pytest fixture:
   ##### Complete initialization fixture
   ```python
   @pytest.fixture
   def living_room(given_that):
        living_room = LivingRoom(None, None, None, None, None, None, None, None)
        living_room.initialize()
        given_that.mock_functions_are_cleared()
        return living_room
   ```
   > ##### Steps breakdown
   >  1. **Create** the instance 
   >     * `living_room = LivingRoom((None, None, None, None, None, None, None, None)`
   >     * Don't worry about all these `None` dependencies, they're mocked by the framework
   >  1. **Replicate Appdaemon lifecycle** by calling `living_room.initialize()`
   >  1. **Reset mock functions** that might have been called during the previous step:  
   >     `given_that.mock_functions_are_cleared()`
1. **Write your first test:**
   ##### Our first unit test
   ```python
   def test_during_night_light_turn_on(given_that, living_room, assert_that):
       given_that.state_of('sensor.living_room_illumination').is_set_to(200) # 200lm == night
       living_room._new_motion(None, None, None)
       assert_that('light.living_room').was.turned_on()
   ```
   > ##### Note
   > The following fixtures are **injected** by pytest using the **[`conftest.py`](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/master/conftest.py) file** and the **initialisation fixture created at Step 1**:
   > * `living_room`
   > * `given_that`
   > * `assert_that`
   > * `time_travel` (Optionally)

### Result
```python
# Important:
# For this example to work, do not forget to copy the `conftest.py` file.

@pytest.fixture
def living_room(given_that):
    living_room = LivingRoom(None, None, None, None, None, None, None, None)
    living_room.initialize()
    given_that.mock_functions_are_cleared()
    return living_room


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
### 1. Set the stage to prepare for the test: `given_that`
*    #### Simulate args passed via `apps.yaml` config
     See: [Appdaemon - Passing arguments to Apps](http://appdaemon.readthedocs.io/en/latest/APPGUIDE.html#passing-arguments-to-apps)
     ```python
     # Command
     given_that.passed_arg(ARG_KEY).is_set_to(ARG_VAL)

     # Example
     given_that.passed_arg('color').is_set_to('blue')
     ```

*    #### State
     ```python
     # Command
     given_that.state_of(ENTITY_ID).is_set_to(STATE_TO_SET)

     # Example
     given_that.state_of(media_player.speaker).is_set_to('playing')
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

> #### Note
> It is best-practice to have an initial test that will test the callbacks
> are _actually_ registered as expected during the `initialize()` phase.  
>
> _For now you need to use direct call to the mocked `hass_functions`_  
> _See: [Full example — Kitchen](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/master/doc/full_example/tests/test_kitchen.py#L41) & [Direct call to `hass_functions`](#direct-call-to-mocked-functions)_



### 3. Assert on your way out: `assert_that`

*    #### Entities
     ```python
     # Available commmands
     assert_that(ENTITY_ID).was.turned_on(OPTIONAL_KWARGS)
     assert_that(ENTITY_ID).was.turned_off()
     assert_that(ENTITY_ID).was_not.turned_on(OPTIONAL_KWARGS)
     assert_that(ENTITY_ID).was_not.turned_off()

     # Examples
     assert_that('light.living_room').was.turned_on()
     assert_that('light.living_room').was.turned_on(color_name=SHOWER_COLOR)
     assert_that('light.living_room').was_not.turned_off()
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
Let's be pragmatic, with that kind of project we're developing for our home, and we're a team of one.
While being a huge proponent for [clean architecture](https://floriankempenich.com/post/11), I believe using such a complex architecture for such a simple project would only result in bringing more complexity than necessary._

### Enjoy the simplicity

Every Automation in Appdaemon follows the same model:
* **Inherit** from **`hass.Hass`**
* **Call** Appdaemon API through **`self`**

**AppdaemonTestFramework** captures all calls to the API and helpers make use of the information to implement common functionality needed in our tests.

Methods from the `hass.Hass` class are patched globally, and injected in the helper classes.
This is done with the `patch_hass()` wich returns a tuple containing:

1. **`hass_functions`**: **dictionary** with all patched functions
1. **`unpatch_callback`**: **callback** to un-patch all patched functions

**`hass_functions`** are injected in the helpers when creating their instances.
After all tests, **`unpatch_callback`** is used to un-patch all patched functions.

Setup and teardown are handled in the [`conftest.py`](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/master/conftest.py) file.



#### Appdaemon Test Framework flow
###### 1. Setup
* **Patch** `hass.Hass` functions
* **Inject** `hass_functions` in helpers: `given_that`, `assert_that`, `time_travel`
###### 2. Test run
* **Run** the test suite
###### 3. Teardown
* **Un-patch** `hass.Hass` functions


## Advanced Usage
### Without `pytest`
If you do no wish to use `pytest`, first maybe reconsider, `pytest` is awesome :)  
If you're really set on using something else, worry not it's pretty straighforward too ;)

What the [`conftest.py`](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/master/conftest.py) file is doing is simply handling the setup & teardown, as well as providing the helpers as injectable fixtures.
It is pretty easy to replicate the same behavior with your test framework of choice. For instance, with `unittest` a base `TestCase` can replace pytest [`conftest.py`](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/master/conftest.py). See the [Unittest Example](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/master/doc/unittest_example.py)

### Direct call to mocked functions
> /!\ WARNING — EXPERIMENTAL /!\

**Want a functionality not implemented by the helpers?**  
You can inject `hass_functions` directly in your tests, patched functions are `MagicMocks`.
The list of patched functions can be found in the [**`init_framework` module**](https://github.com/FlorianKempenich/Appdaemon-Test-Framework/blob/master/appdaemontestframework/init_framework.py#L60).




---
## Author Information
Follow me on Twitter: [@ThisIsFlorianK](https://twitter.com/ThisIsFlorianK)  
Find out more about my work: [Florian Kempenich — Personal Website](https://floriankempenich.com)
