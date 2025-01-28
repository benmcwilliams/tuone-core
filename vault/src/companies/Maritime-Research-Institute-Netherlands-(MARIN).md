```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Maritime-Research-Institute-Netherlands-(MARIN)" or company = "Maritime Research Institute Netherlands (MARIN)")
sort location, dt_announce desc
```
