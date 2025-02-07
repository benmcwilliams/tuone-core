```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Bristol-Robotics-Laboratory" or company = "Bristol Robotics Laboratory")
sort location, dt_announce desc
```
