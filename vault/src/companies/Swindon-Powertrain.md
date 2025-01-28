```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Swindon-Powertrain" or company = "Swindon Powertrain")
sort location, dt_announce desc
```
