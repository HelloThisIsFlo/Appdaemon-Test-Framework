import appdaemon.plugins.hass.hassapi as hass

class HelloWorld(hass.Hass):
    def initialize(self):
      self.log("initialized")
      self.listen_state(self.listen_pole_light, "light.pole_a")
    
    def listen_pole_light(self, entity, attribute, old, new, kwargs):
      self.log("Running callback :)")
      self.log(entity)
      self.log(attribute)
      self.log(old)
      self.log(new)
      self.log(kwargs)
      bed_light = "light.bed_a"
      if new == 'on':
        self.turn_on(bed_light)
      elif new == 'off':
        self.turn_off(bed_light)

