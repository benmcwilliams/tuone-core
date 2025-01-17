```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and location = "Rheinmetall's Sensors and Actuators Division"
sort company, dt_announce desc
```
