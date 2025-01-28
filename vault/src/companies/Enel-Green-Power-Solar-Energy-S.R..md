```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Enel-Green-Power-Solar-Energy-S.R." or company = "Enel Green Power Solar Energy S.R.")
sort location, dt_announce desc
```
