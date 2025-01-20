```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and location = "Robotics and AI Collaboration centre (RAICo1)"
sort company, dt_announce desc
```
