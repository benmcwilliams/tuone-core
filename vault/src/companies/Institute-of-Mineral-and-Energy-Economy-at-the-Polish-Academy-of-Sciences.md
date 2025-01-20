```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "Institute of Mineral and Energy Economy at the Polish Academy of Sciences"
sort location, dt_announce desc
```
