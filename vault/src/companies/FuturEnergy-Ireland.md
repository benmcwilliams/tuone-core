```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "FuturEnergy-Ireland" or company = "FuturEnergy Ireland")
sort location, dt_announce desc
```
