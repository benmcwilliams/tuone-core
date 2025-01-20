```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "Institute of Science of Food Production C.N.R. Unit of Lecce"
sort location, dt_announce desc
```
