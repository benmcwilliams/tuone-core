```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Energyra-B.V" or company = "Energyra B.V")
sort location, dt_announce desc
```
