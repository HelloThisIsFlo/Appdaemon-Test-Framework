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

    # At T=5min light should been have turned off
    time_travel.fast_forward(1).minutes()    
    time_travel.assert_current_time(5).minutes()
    assert_that('light.bathroom').was.turned_off()
```

---

## 5-Minutes Quick Start Guide
### Initial Setup
1. Install **pytest**: `pip install pytest`
1. Install **framework**: `pip install appdaemontestframework`
1. Copy `conftest.py` at the **root** of your project

### Write you first unit test
Let's test an Appdaemon automation we created, which, say, handles automatic lighting in the Living Room: `class LivingRoom`  
<!-- We called the class `LivingRoom`. Since it's an Appdaemon automation its lifecycle is handled  -->

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
   > The following fixtures are **injected** by pytest using the **`conftest.py` file** and the **initialisation fixture created at Step 1**:
   > * `living_room`
   > * `given_that`
   > * `assert_that`
   > * `time_travel` (Optionally)


---
## Available commands
### `given_that`
* `asdfads`
* `asdfads`
* `asdfads`
### `assert_that`
* `asdfads`
* `asdfads`
### `time_travel`
* `asdfads`
* `asdfads`

---
## Under The Hood
EXPLAIN HERE HOW IT WORKS
EXPLAIN HERE HOW IT WORKS
EXPLAIN HERE HOW IT WORKS

---
## Advanced Usage
### No `pytest`
asdfasd

### Direct call to mocked functions
Inject `hass_functions` bla bla bla


# TODO
---
**Notes:**
Explanation of `conftest.py`: https://docs.pytest.org/en/latest/fixture.html?highlight=conftest#conftest-py-sharing-fixture-functions

