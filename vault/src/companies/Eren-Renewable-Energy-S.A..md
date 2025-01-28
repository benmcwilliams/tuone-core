```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Eren-Renewable-Energy-S.A." or company = "Eren Renewable Energy S.A.")
sort location, dt_announce desc
```
