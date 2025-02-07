```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Horiba-FuelCon" or company = "Horiba FuelCon")
sort location, dt_announce desc
```
