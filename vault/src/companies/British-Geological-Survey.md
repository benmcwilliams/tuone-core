```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "British-Geological-Survey" or company = "British Geological Survey")
sort location, dt_announce desc
```
