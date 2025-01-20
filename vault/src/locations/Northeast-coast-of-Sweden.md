```dataview
table company, tech, component, status, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and location = "Northeast coast of Sweden"
sort company, dt_announce desc
```
