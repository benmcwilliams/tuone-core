```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "TMK-Hydroenergy-Power" or company = "TMK Hydroenergy Power")
sort location, dt_announce desc
```
