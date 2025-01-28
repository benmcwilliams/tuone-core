```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Colway-Energia" or company = "Colway Energia")
sort location, dt_announce desc
```
