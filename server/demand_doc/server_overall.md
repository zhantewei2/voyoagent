我们的voyoagent是支持很多比如registry_mcp , registry_tool , registry_skill的。所以我们都可以将这些数据放入pg中，我们这个server其实属于agent管理平台。

这里我们有几大模块：
  1. 模型管理；
  2. skill管理; 
  3. mcp管理； 
  4. tool管理（因为tool内置原因，tool管理界面只能查看list与tool详情）。
   1 2 3  三个模块支持列表，详情，删除，新增，修改（查看详情不要跳转页面，而是modal弹出层查看详情）。 
   
  5. 然后有一个Agent管理界面，这里我们可以创建Agent, 查看，删除，更新agent。  已经调试agent(在agent列表中，点击后进入详情页，左侧是Agent的相关配置，比如提示词，装配的tool， mcp, skill，使用的model， 右侧是对话框，可以与agent聊天)。这个详情页的右上方会有一个 api接口按钮， 点击后 modal 弹窗可以查看当前agent暴露出来的 api接口（域名取当前域名,前端处理，路径则是固定的chat路径，然后?agent={agentId}），这个api接口提供是否关闭thinking，只提供stream接口，这与我们的voyoagent保持一致。

我们主要实现上方功能，不用做用户登录管理。

你按照yo-dev-xxl的要求来完成任务，但注意，只要使用一个subagent即可。 即设计文档与代码文档你出，然后这个subagent来完成前后端的任务与测试。你负责引导它即可。

代码编写注意：
- 不需要每个大功能都新创建一个subagent， 这样会导致每次大功能subagent都重新阅读项目，非常耗时。你只要持续与subagent沟通即可，你负责引导它完成任务，但它完成一项任务后，不要关闭它，你引导它的后续工作。
- 注意测试用例，要求它写简单写，主要关注重要功能，不要写太细了。

功能点注意：

- 聊天记录可以存入放pg表中，这样用户调用统一chat_id时，就可以从pg中捞回聊天记录推入history中。 一段聊天记录作为text字段以json格式，存入一个字段中即可。聊天前，先使用接口创建聊天id ,当没有聊天id时。

- 注意agent的详情中，我们可以管理agent的soul提示词。对应的是soul.md，而不是system.md，system.md是不允许被应用端修改的。