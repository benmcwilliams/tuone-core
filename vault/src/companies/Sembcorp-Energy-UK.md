```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Sembcorp-Energy-UK" or company = "Sembcorp Energy UK")
sort location, dt_announce desc
```
