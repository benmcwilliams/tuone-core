```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Offshore-Renewable-Energy-Catapult" or company = "Offshore Renewable Energy Catapult")
sort location, dt_announce desc
```
