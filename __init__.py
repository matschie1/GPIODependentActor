import time
from modules import cbpi
from modules.core.hardware import SensorActive
from modules.core.props import Property
import requests
from modules.core.props import Property
from modules.core.hardware import ActorBase

cbpi.GPIODependentActors = []

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
except Exception as e:
    print e
    pass

@cbpi.actor
class GPIODependentActor(ActorBase):
    base = Property.Actor(label="Base Actor", description="Select the actor you would like to add a dependency to.")
    dependent_gpio = Property.Select("Dependent GPIO", options=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27])
    dependency_type = Property.Select(label="Dependency Type", options=["HIGH", "LOW"], description="Select the dependency type. With 'HIGH', the 'GPIO' is required to be HIGH in order to switch the 'Base Actor' ON. With 'LOW', the 'GPIO' is required to be LOW in order to switch the 'Base Actor' ON.")
    timeout = Property.Number("Notification duration (ms)", True, 5000, description="0ms will disable notifications completely")
    actor_shouldbeon = False
    actor_ison = False
    actor_flagbackground = False

    def init(self):
        GPIO.setup(int(self.dependent_gpio), GPIO.IN , pull_up_down = GPIO.PUD_DOWN)
        super(GPIODependentActor, self).init()
        cbpi.GPIODependentActors += [self]

    def set_power(self, power):
        self.api.actor_power(int(self.base), power=power)

    def off(self):
        self.api.switch_actor_off(int(self.base))
        self.actor_shouldbeon = False
        self.actor_ison = False

    def on(self, power=None):
        self.actor_shouldbeon = True
        if GPIO.input(int(self.dependent_gpio)) == 0:
            if self.dependency_type == "HIGH":
                if self.actor_ison:
                    self.api.switch_actor_off(int(self.base))
                    self.actor_ison = False
                    if self.timeout > 0.0:
                        self.api.notify("Actor turned off", "Actor turned off because dependent PIN turned LOW", type="warning", timeout=self.timeout)
                elif not self.actor_flagbackground and self.timeout > 0.0:
                    self.api.notify("Actor not turned on", "Actor was not turned on because dependent PIN is LOW", type="warning", timeout=self.timeout)
            elif self.dependency_type == "LOW":
                if not self.actor_ison:
                    self.api.switch_actor_on(int(self.base), power=power)
                    self.actor_ison = True
                    if self.actor_flagbackground and self.timeout > 0.0:
                        self.api.notify("Actor turned on", "Actor turned on because dependent PIN turned LOW", type="success", timeout=self.timeout)
        elif GPIO.input(int(self.dependent_gpio)) == 1:
            if self.dependency_type == "HIGH":
                if not self.actor_ison:
                    self.api.switch_actor_on(int(self.base), power=power)
                    self.actor_ison = True
                    if self.actor_flagbackground and self.timeout > 0.0:
                        self.api.notify("Actor turned on", "Actor turned on because dependent PIN turned HIGH", type="success", timeout=self.timeout)
            elif self.dependency_type == "LOW":
                if self.actor_ison:
                    self.api.switch_actor_off(int(self.base))
                    self.actor_ison = False
                    if self.timeout > 0.0:
                        self.api.notify("Actor turned off", "Actor turned off because dependent PIN turned HIGH", type="warning", timeout=self.timeout)
                elif not self.actor_flagbackground and self.timeout > 0.0:
                    self.api.notify("Actor not turned on", "Actor was not turned on because dependent PIN is HIGH", type="warning", timeout=self.timeout)
        self.actor_flagbackground = False

@cbpi.backgroundtask(key="update_GPIODependentActors", interval=1)
def update_GPIODependentActors(api):
    for gpiodependentactor in cbpi.GPIODependentActors:
        if gpiodependentactor.actor_shouldbeon:
            gpiodependentactor.actor_flagbackground = True
            gpiodependentactor.on()
