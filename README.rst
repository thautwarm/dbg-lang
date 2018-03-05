
DBG
===================

我真的好讨厌网站开发，花Q.

.. code ::
    
    User(id: int~)   # 主键 id, 使用 sequence
    {
        openid    : TextStr?                   # 可空
        account   : NameStr!                   # 唯一。 
                                               # 后缀描述符可叠加 例如 account: NameStr?!
        password  : NameStr   
        permission: Permission
        sex       : Sex         = Sex.unknown  # 默认值
        nickname  : NameStr?
        repr{
            id, nickname, permission
        }
    }

    Item(id: int~){
        name: NameStr?
        cost: int

        repr = all
    }

    Course(id: int~){
        location: NameStr?
        time_seq: TinyStr

        repr = all
    }

    Some(id: int~){
        name: NameStr!

        repr{

        }

    }

    User^ <-> Item{     # 一对一关系， User对Item具有所有权
        some: NameStr?  # extra data
    }

    User <<->> Course{  # 多对多关系
        
    }

    User <<-> Some{     # 多对一关系

    }


Downlaod & Usage
========================


.. code :: shell

    pip install git+https://github.com/thautwarm/dbg-lang.git@master && cd dbg-lang/

    dbgc db.dbg out.py import "* from customs"





