```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "NextEnergy-Solar-Fund" or company = "NextEnergy Solar Fund")
sort location, dt_announce desc
```
