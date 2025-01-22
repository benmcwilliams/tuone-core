```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where company = "Farasis Energy"
sort location, dt_announce desc
```
