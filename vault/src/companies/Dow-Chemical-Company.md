```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Dow-Chemical-Company" or company = "Dow Chemical Company")
sort location, dt_announce desc
```
