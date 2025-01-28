```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Pylon-LifeEU" or company = "Pylon LifeEU")
sort location, dt_announce desc
```
